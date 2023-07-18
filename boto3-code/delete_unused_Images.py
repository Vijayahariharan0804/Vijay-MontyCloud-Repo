import boto3
from pprint import pprint
#all launch_list file('image-id.txt') appending image_id in the list (all_image_lst)
all_image_lst = []
with open('image-id.txt', 'r') as file:
    all_image_lst = [line.strip() for line in file]

aws_profile = 'default'
session = boto3.Session(profile_name = aws_profile, region_name= 'us-east-1')

#getting the region as input:
region=input(str("enter the region:"))
ec2_client = session.client('ec2',region)

#fetching the ami that are attached with the ec2 and creating the list (lst):
response=ec2_client.describe_instances()
Reservations=response['Reservations']
ec2_ami_lst=[]
for each in Reservations:
    for each1 in each['Instances']:
        a=each1['ImageId']
        ec2_ami_lst.append(a)
image_used_in_ec2 = list(set(all_image_lst).intersection(ec2_ami_lst))
image_not_used_in_ec2 = list(set(all_image_lst).symmetric_difference(ec2_ami_lst))
print("images used in ec2")
print(image_used_in_ec2)
print("images not_used in ec2")
print(image_not_used_in_ec2)
#ec2_images==images matched images meta_data of instances
ec2_meta_data_lst=[]
print(" Matched images meta_data of instances ec2_images==images")
for i in image_used_in_ec2:
    image_id=i
    response1 = ec2_client.describe_instances(Filters=[ {'Name': 'image-id', 'Values': [image_id] }   ] )
    Reservations=response1['Reservations']
    for each in Reservations:
        a= each['Instances']
        for each1 in a:
           ImageId=each1['ImageId']
           InstanceId=each1['InstanceId']
           InstanceType=each1['InstanceType']
           response1=each1['Tags']
           for tag in response1:
              if tag['Key'] == 'Name':
                 name = tag['Value']
                 break
           PlatformDetails=each1['PlatformDetails']
           meta_data=(f"{name},{ImageId},{InstanceId},{InstanceType},{PlatformDetails}")
           ec2_meta_data_lst.append(meta_data)
#print("\n",ec2_meta_data_lst)
print("writing the meta_data of used ami ec2 instances in the file-->meta_ec2_file.txt")           
#creating file to store meta_data of ec2:
file1 = open('meta_ec2_file.txt','w')
for data in ec2_meta_data_lst:
    file1.write(data+"\n")         

autoscaling_client = session.client('autoscaling',region)
#fetching the ami that are attached with the ASG and creating the list (lst):
response3=autoscaling_client.describe_auto_scaling_groups()
AutoScalingGroups=response3['AutoScalingGroups']
lst1=[]
#LISTING all auto scaling groups and fetching the launch_templete details 
for i in AutoScalingGroups:
    AutoScalingGroupName=i['AutoScalingGroupName']
    LaunchTemplate=i['LaunchTemplate']
    LaunchTemplateId=LaunchTemplate['LaunchTemplateId']
    LaunchTemplateName=LaunchTemplate['LaunchTemplateName']
    Version=LaunchTemplate['Version']
    response1=ec2_client.describe_launch_template_versions(LaunchTemplateId=LaunchTemplateId)
    LaunchTemplateVersions=response1['LaunchTemplateVersions']
    for i in LaunchTemplateVersions:
        ImageId=i['LaunchTemplateData']['ImageId']
        VersionNumber=i['VersionNumber']
        LaunchTemplateName=i['LaunchTemplateName']
        lst1.append(ImageId)
    print("\n")
    print("Launch_Template_Ami that are used by Asg")
    Asg_UsedImage_lst=list(set(all_image_lst).intersection(lst1))
    print(Asg_UsedImage_lst)
    print("Launch_Template_Ami that are not used by Asg")
    Asg_NotUsedImage_lst=list(set(all_image_lst).symmetric_difference(lst1))
    print(Asg_NotUsedImage_lst)
    print("\n")
#Meta_data of the matched sg_UsedImage_lst:
for i in AutoScalingGroups:
    LaunchTemplate=i['LaunchTemplate']
    LaunchTemplateId=LaunchTemplate['LaunchTemplateId']
    AutoScalingGroupName=i['AutoScalingGroupName']
    print("AutoScalingGroupName is:",AutoScalingGroupName)
    print("LaunchTemplateName is:",LaunchTemplateName)  
    for i in Asg_UsedImage_lst:
        response3 = ec2_client.describe_launch_template_versions(LaunchTemplateId=LaunchTemplateId,Filters=[{'Name': 'image-id','Values': [i]}])
        LaunchTemplateVersions=response3['LaunchTemplateVersions']
        for i in LaunchTemplateVersions:
            ImageId=i['LaunchTemplateData']['ImageId']
            VersionNumber=i['VersionNumber']
            LaunchTemplateName=i['LaunchTemplateName']
            print(f"version is:{VersionNumber},image_id is:{ImageId}")
#deregister and deleting the all unused Images:
all_Unused_AMI=set(image_not_used_in_ec2+Asg_NotUsedImage_lst)
print("deregister and deleting the all unused Images")
print(all_Unused_AMI)
all_Unused_IMAGES=list(set(all_image_lst).intersection(all_Unused_AMI))
print("ALL UNUSED IMAGES ARE:",all_Unused_IMAGES)



snapshot_id_lst=[]
for i in all_Unused_IMAGES:
   response7= ec2_client.describe_images(Filters=[ {'Name': 'image-id', 'Values': [i] } ] )
   Images=response7['Images']
   for i in Images:
        BlockDeviceMappings=i['BlockDeviceMappings']
        for j in BlockDeviceMappings:
            if 'Ebs' in j:
                ebs = j['Ebs']
                SnapshotId=(ebs['SnapshotId'])
                print(SnapshotId)
                snapshot_id_lst.append(SnapshotId)
for i in all_Unused_IMAGES:
    response = ec2_client.deregister_image(ImageId=i)
    print("images deleted successfully")
for i in snapshot_id_lst:              
    response = ec2_client.delete_snapshot(SnapshotId=i)
    print("snapshot deleted sucessfully")